#!/usr/bin/env python3
"""
Typography Issues Fix Script
Systematically fixes critical typography issues in React components and landing page
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

class TypographyFixer:
    def __init__(self):
        self.fixes_applied = []
        self.files_processed = []
        self.backup_dir = f"typography_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def create_backup(self, file_path):
        """Create backup of file before making changes"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        backup_path = os.path.join(self.backup_dir, os.path.basename(file_path))
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def fix_text_sizes(self, file_path):
        """Fix text size issues in a file"""
        try:
            # Create backup
            backup_path = self.create_backup(file_path)
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_made = []
            
            # Fix text-xs to text-base (12px → 16px)
            if 'text-xs' in content:
                content = re.sub(r'\btext-xs\b', 'text-base', content)
                fixes_made.append('text-xs → text-base')
            
            # Fix text-sm to text-base (14px → 16px)
            if 'text-sm' in content:
                content = re.sub(r'\btext-sm\b', 'text-base', content)
                fixes_made.append('text-sm → text-base')
            
            # Fix font-thin to font-normal (100 → 400)
            if 'font-thin' in content:
                content = re.sub(r'\bfont-thin\b', 'font-normal', content)
                fixes_made.append('font-thin → font-normal')
            
            # Fix font-light to font-medium (300 → 500)
            if 'font-light' in content:
                content = re.sub(r'\bfont-light\b', 'font-medium', content)
                fixes_made.append('font-light → font-medium')
            
            # Fix font-extralight to font-normal (200 → 400)
            if 'font-extralight' in content:
                content = re.sub(r'\bfont-extralight\b', 'font-normal', content)
                fixes_made.append('font-extralight → font-normal')
            
            # Write changes if any fixes were made
            if fixes_made:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.append({
                    'file': file_path,
                    'backup': backup_path,
                    'fixes': fixes_made,
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"✅ Fixed {len(fixes_made)} issues in {os.path.basename(file_path)}")
                for fix in fixes_made:
                    print(f"   • {fix}")
            
            self.files_processed.append(file_path)
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    def fix_landing_page(self):
        """Fix typography issues in landing page"""
        landing_file = 'landing.html'
        if os.path.exists(landing_file):
            print(f"\n🔧 Fixing typography issues in {landing_file}...")
            
            try:
                # Create backup
                backup_path = self.create_backup(landing_file)
                
                # Read file content
                with open(landing_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                fixes_made = []
                
                # Fix font-size: 12px to 14px
                if 'font-size: 12px' in content:
                    content = content.replace('font-size: 12px', 'font-size: 14px')
                    fixes_made.append('font-size: 12px → 14px')
                
                # Fix font-size: 14px to 16px
                if 'font-size: 14px' in content:
                    content = content.replace('font-size: 14px', 'font-size: 16px')
                    fixes_made.append('font-size: 14px → 16px')
                
                # Fix line-height issues
                if 'line-height: 1.2' in content:
                    content = content.replace('line-height: 1.2', 'line-height: 1.6')
                    fixes_made.append('line-height: 1.2 → 1.6')
                
                if 'line-height: 1.3' in content:
                    content = content.replace('line-height: 1.3', 'line-height: 1.6')
                    fixes_made.append('line-height: 1.3 → 1.6')
                
                # Write changes if any fixes were made
                if fixes_made:
                    with open(landing_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.fixes_applied.append({
                        'file': landing_file,
                        'backup': backup_path,
                        'fixes': fixes_made,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    print(f"✅ Fixed {len(fixes_made)} issues in {landing_file}")
                    for fix in fixes_made:
                        print(f"   • {fix}")
                
                self.files_processed.append(landing_file)
                
            except Exception as e:
                print(f"❌ Error processing {landing_file}: {e}")
    
    def fix_css_files(self):
        """Fix typography issues in CSS files"""
        css_files = [
            'responsive_typography_system.css',
            'mobile_spacing_system.css'
        ]
        
        for css_file in css_files:
            if os.path.exists(css_file):
                print(f"\n🔧 Fixing typography issues in {css_file}...")
                
                try:
                    # Create backup
                    backup_path = self.create_backup(css_file)
                    
                    # Read file content
                    with open(css_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    fixes_made = []
                    
                    # Fix font-size values
                    if '--font-size-xs: 12px' in content:
                        content = content.replace('--font-size-xs: 12px', '--font-size-xs: 16px')
                        fixes_made.append('--font-size-xs: 12px → 16px')
                    
                    if '--font-size-sm: 14px' in content:
                        content = content.replace('--font-size-sm: 14px', '--font-size-sm: 18px')
                        fixes_made.append('--font-size-sm: 14px → 18px')
                    
                    # Fix line-height values
                    if '--line-height-tight: 1.2' in content:
                        content = content.replace('--line-height-tight: 1.2', '--line-height-tight: 1.4')
                        fixes_made.append('--line-height-tight: 1.2 → 1.4')
                    
                    if '--line-height-normal: 1.4' in content:
                        content = content.replace('--line-height-normal: 1.4', '--line-height-normal: 1.6')
                        fixes_made.append('--line-height-normal: 1.4 → 1.6')
                    
                    # Write changes if any fixes were made
                    if fixes_made:
                        with open(css_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        self.fixes_applied.append({
                            'file': css_file,
                            'backup': backup_path,
                            'fixes': fixes_made,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        print(f"✅ Fixed {len(fixes_made)} issues in {css_file}")
                        for fix in fixes_made:
                            print(f"   • {fix}")
                    
                    self.files_processed.append(css_file)
                    
                except Exception as e:
                    print(f"❌ Error processing {css_file}: {e}")
    
    def process_react_components(self):
        """Process all React component files"""
        # Define directories to process
        directories = [
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
        
        total_files = 0
        files_with_fixes = 0
        
        for directory in directories:
            if os.path.exists(directory):
                print(f"\n📁 Processing {directory}...")
                
                # Find all TSX files in directory
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.tsx') or file.endswith('.ts'):
                            file_path = os.path.join(root, file)
                            total_files += 1
                            
                            # Check if file has typography issues
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            if any(issue in content for issue in ['text-xs', 'text-sm', 'font-thin', 'font-light', 'font-extralight']):
                                print(f"🔧 Fixing {file}...")
                                self.fix_text_sizes(file_path)
                                files_with_fixes += 1
        
        print(f"\n📊 Summary:")
        print(f"   • Total files processed: {total_files}")
        print(f"   • Files with fixes: {files_with_fixes}")
        print(f"   • Total fixes applied: {len(self.fixes_applied)}")
    
    def generate_report(self):
        """Generate a report of all fixes applied"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files_processed': len(self.files_processed),
                'total_fixes_applied': len(self.fixes_applied),
                'backup_directory': self.backup_dir
            },
            'fixes': self.fixes_applied
        }
        
        # Save report
        report_filename = f"typography_fixes_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Fix report saved to: {report_filename}")
        print(f"📁 Backups saved to: {self.backup_dir}")
        
        return report

def main():
    """Main function to run typography fixes"""
    print("🔧 Typography Issues Fix Script")
    print("=" * 50)
    print("Fixing critical typography issues for mobile readability")
    print("=" * 50)
    
    fixer = TypographyFixer()
    
    # Fix landing page
    fixer.fix_landing_page()
    
    # Fix CSS files
    fixer.fix_css_files()
    
    # Fix React components
    fixer.process_react_components()
    
    # Generate report
    report = fixer.generate_report()
    
    print("\n" + "=" * 50)
    print("✅ TYPOGRAPHY FIXES COMPLETE")
    print("=" * 50)
    
    print(f"📊 Summary:")
    print(f"   • Files processed: {report['summary']['total_files_processed']}")
    print(f"   • Fixes applied: {report['summary']['total_fixes_applied']}")
    print(f"   • Backup directory: {report['summary']['backup_directory']}")
    
    if report['fixes']:
        print(f"\n🔧 Fixes Applied:")
        for fix in report['fixes']:
            print(f"   • {os.path.basename(fix['file'])}: {', '.join(fix['fixes'])}")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Test the application on mobile devices")
    print(f"   2. Verify readability improvements")
    print(f"   3. Run accessibility tests")
    print(f"   4. If issues arise, restore from backup directory")

if __name__ == "__main__":
    main()
