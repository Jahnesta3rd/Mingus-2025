#!/usr/bin/env python3
"""
Touch Target Fixes Application Script
Automatically applies touch target optimizations to HTML files
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Tuple

class TouchTargetFixer:
    """Applies touch target optimizations to HTML files"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.fixes_applied = 0
        self.files_processed = 0
        
        # Touch target class mappings
        self.class_mappings = {
            # Navigation elements
            r'<a([^>]*class="[^"]*nav-link[^"]*)"([^>]*)>': r'<a\1 btn-primary"\2>',
            r'<a([^>]*class="[^"]*nav-item[^"]*)"([^>]*)>': r'<a\1 btn-primary"\2>',
            
            # CTA buttons
            r'<button([^>]*class="[^"]*btn[^"]*)"([^>]*)>': r'<button\1 btn-cta btn-primary"\2>',
            r'<a([^>]*class="[^"]*cta[^"]*)"([^>]*)>': r'<a\1 btn-cta btn-primary"\2>',
            
            # Calculator buttons
            r'<button([^>]*class="[^"]*calc[^"]*)"([^>]*)>': r'<button\1 calculator-button btn-number"\2>',
            r'<button([^>]*class="[^"]*calculator[^"]*)"([^"]*)"([^>]*)>': r'<button\1 calculator-button btn-number"\2>',
            
            # Form elements
            r'<input([^>]*type="text"[^>]*)>': r'<input\1 class="form-input">',
            r'<input([^>]*type="email"[^>]*)>': r'<input\1 class="form-input">',
            r'<input([^>]*type="password"[^>]*)>': r'<input\1 class="form-input">',
            r'<select([^>]*)>': r'<select\1 class="form-input">',
            r'<textarea([^>]*)>': r'<textarea\1 class="form-input">',
        }
        
        # HTML files to process
        self.html_patterns = [
            "**/*.html",
            "**/*.htm",
            "templates/**/*.html",
            "frontend/**/*.html",
            "public/**/*.html"
        ]
    
    def find_html_files(self) -> List[Path]:
        """Find all HTML files in the project"""
        html_files = []
        
        for pattern in self.html_patterns:
            files = glob.glob(pattern, recursive=True)
            html_files.extend([Path(f) for f in files if Path(f).is_file()])
        
        # Remove duplicates and sort
        html_files = list(set(html_files))
        html_files.sort()
        
        return html_files
    
    def apply_fixes_to_file(self, file_path: Path) -> int:
        """Apply touch target fixes to a single HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_in_file = 0
            
            # Apply each fix pattern
            for pattern, replacement in self.class_mappings.items():
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    fixes_in_file += len(matches)
            
            # Add CSS import if not present
            if 'touch_target_optimization.css' not in content:
                css_import = '    <link rel="stylesheet" href="touch_target_optimization.css">\n'
                
                # Find head tag and insert CSS import
                if '<head>' in content:
                    content = content.replace('<head>', f'<head>\n{css_import}', 1)
                elif '<html>' in content:
                    content = content.replace('<html>', f'<html>\n<head>\n{css_import}</head>', 1)
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return fixes_in_file
            
            return 0
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return 0
    
    def validate_touch_targets(self, file_path: Path) -> Dict[str, any]:
        """Validate touch target compliance in an HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            validation = {
                'file': str(file_path),
                'total_elements': 0,
                'compliant_elements': 0,
                'issues': [],
                'score': 0.0
            }
            
            # Count interactive elements
            button_patterns = [
                r'<button[^>]*>',
                r'<a[^>]*class="[^"]*btn[^"]*"[^>]*>',
                r'<input[^>]*type="(button|submit|reset)"[^>]*>',
                r'<select[^>]*>',
                r'<textarea[^>]*>'
            ]
            
            for pattern in button_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                validation['total_elements'] += len(matches)
            
            # Check for proper classes
            compliant_patterns = [
                r'class="[^"]*(btn-primary|btn-cta|calculator-button|form-input)[^"]*"',
                r'min-height:\s*44px',
                r'min-width:\s*44px'
            ]
            
            for pattern in compliant_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                validation['compliant_elements'] += len(matches)
            
            # Calculate score
            if validation['total_elements'] > 0:
                validation['score'] = (validation['compliant_elements'] / validation['total_elements']) * 100
            
            return validation
            
        except Exception as e:
            return {
                'file': str(file_path),
                'error': str(e),
                'score': 0.0
            }
    
    def run_fixes(self) -> Dict[str, any]:
        """Run all touch target fixes"""
        print("🚀 Starting Touch Target Fixes Application")
        print("=" * 60)
        
        html_files = self.find_html_files()
        print(f"📁 Found {len(html_files)} HTML files to process")
        
        results = {
            'files_processed': 0,
            'total_fixes': 0,
            'validation_results': [],
            'summary': {}
        }
        
        for file_path in html_files:
            print(f"\n📄 Processing: {file_path}")
            
            # Apply fixes
            fixes = self.apply_fixes_to_file(file_path)
            if fixes > 0:
                print(f"   ✅ Applied {fixes} fixes")
                results['total_fixes'] += fixes
            
            # Validate results
            validation = self.validate_touch_targets(file_path)
            results['validation_results'].append(validation)
            
            if 'error' not in validation:
                print(f"   📊 Compliance Score: {validation['score']:.1f}%")
            
            results['files_processed'] += 1
        
        # Generate summary
        if results['validation_results']:
            scores = [r['score'] for r in results['validation_results'] if 'error' not in r]
            if scores:
                results['summary'] = {
                    'average_score': sum(scores) / len(scores),
                    'min_score': min(scores),
                    'max_score': max(scores),
                    'files_above_95': len([s for s in scores if s >= 95]),
                    'total_files': len(scores)
                }
        
        return results
    
    def print_summary(self, results: Dict[str, any]):
        """Print a summary of the fixes applied"""
        print("\n" + "=" * 60)
        print("📋 TOUCH TARGET FIXES SUMMARY")
        print("=" * 60)
        
        print(f"📁 Files Processed: {results['files_processed']}")
        print(f"🔧 Total Fixes Applied: {results['total_fixes']}")
        
        if results['summary']:
            summary = results['summary']
            print(f"📊 Average Compliance Score: {summary['average_score']:.1f}%")
            print(f"🎯 Files Above 95%: {summary['files_above_95']}/{summary['total_files']}")
            print(f"📈 Score Range: {summary['min_score']:.1f}% - {summary['max_score']:.1f}%")
        
        print("\n💡 Next Steps:")
        print("1. Test your application with the new touch target optimizations")
        print("2. Run touch interaction testing: python3 touch_interaction_tester.py --url http://localhost:5003")
        print("3. Verify 95%+ compliance has been achieved")
        print("4. Test on actual mobile devices for best results")

def main():
    """Main function"""
    print("🎯 Touch Target Compliance Fixer")
    print("Achieving 95%+ touch target compliance for mobile applications")
    print()
    
    # Initialize fixer
    fixer = TouchTargetFixer()
    
    # Run fixes
    results = fixer.run_fixes()
    
    # Print summary
    fixer.print_summary(results)
    
    # Save results
    import json
    from datetime import datetime
    
    results_file = f"touch_target_fixes_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    main()
