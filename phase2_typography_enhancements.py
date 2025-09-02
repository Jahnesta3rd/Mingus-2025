#!/usr/bin/env python3
"""
Phase 2 Typography Enhancements
Implements line heights, CTA typography, and heading hierarchy improvements
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

class Phase2TypographyEnhancer:
    def __init__(self):
        self.enhancements_applied = []
        self.files_processed = []
        self.backup_dir = f"phase2_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def create_backup(self, file_path):
        """Create backup of file before making changes"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        backup_path = os.path.join(self.backup_dir, os.path.basename(file_path))
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def enhance_line_heights(self, file_path):
        """Enhance line heights for better mobile readability"""
        try:
            # Create backup
            backup_path = self.create_backup(file_path)
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            enhancements_made = []
            
            # Enhance line heights for better mobile readability
            if 'leading-tight' in content:
                content = re.sub(r'\bleading-tight\b', 'leading-relaxed', content)
                enhancements_made.append('leading-tight → leading-relaxed')
            
            if 'leading-snug' in content:
                content = re.sub(r'\bleading-snug\b', 'leading-normal', content)
                enhancements_made.append('leading-snug → leading-normal')
            
            # Add line-height to text-base classes for better readability
            if 'text-base' in content and 'leading-' not in content:
                # Find text-base classes and add leading-relaxed
                content = re.sub(r'\btext-base\b', 'text-base leading-relaxed', content)
                enhancements_made.append('Added leading-relaxed to text-base')
            
            # Write changes if any enhancements were made
            if enhancements_made:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.enhancements_applied.append({
                    'file': file_path,
                    'backup': backup_path,
                    'enhancements': enhancements_made,
                    'type': 'line_height',
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"✅ Enhanced line heights in {os.path.basename(file_path)}")
                for enhancement in enhancements_made:
                    print(f"   • {enhancement}")
            
            self.files_processed.append(file_path)
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    def enhance_cta_typography(self, file_path):
        """Enhance CTA typography for better prominence"""
        try:
            # Create backup
            backup_path = self.create_backup(file_path)
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            enhancements_made = []
            
            # Enhance button typography
            button_patterns = [
                (r'className="([^"]*btn[^"]*)"', r'className="\1 font-semibold text-lg"'),
                (r'className="([^"]*button[^"]*)"', r'className="\1 font-semibold text-lg"'),
                (r'className="([^"]*cta[^"]*)"', r'className="\1 font-semibold text-lg"')
            ]
            
            for pattern, replacement in button_patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    enhancements_made.append('Enhanced button typography')
                    break
            
            # Enhance link typography
            link_patterns = [
                (r'<a[^>]*className="([^"]*)"[^>]*>([^<]+)</a>', r'<a \1 className="\1 font-medium text-base">\2</a>')
            ]
            
            for pattern, replacement in link_patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    enhancements_made.append('Enhanced link typography')
                    break
            
            # Write changes if any enhancements were made
            if enhancements_made:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.enhancements_applied.append({
                    'file': file_path,
                    'backup': backup_path,
                    'enhancements': enhancements_made,
                    'type': 'cta_typography',
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"✅ Enhanced CTA typography in {os.path.basename(file_path)}")
                for enhancement in enhancements_made:
                    print(f"   • {enhancement}")
            
            self.files_processed.append(file_path)
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    def enhance_heading_hierarchy(self, file_path):
        """Enhance heading hierarchy for better structure"""
        try:
            # Create backup
            backup_path = self.create_backup(file_path)
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            enhancements_made = []
            
            # Count H1 elements
            h1_count = len(re.findall(r'<h1[^>]*>', content))
            
            # If multiple H1 elements, convert some to H2
            if h1_count > 1:
                # Keep the first H1, convert others to H2
                h1_matches = list(re.finditer(r'<h1([^>]*)>([^<]+)</h1>', content))
                
                for i, match in enumerate(h1_matches[1:], 1):  # Skip first H1
                    old_h1 = match.group(0)
                    new_h2 = f'<h2{match.group(1)}>{match.group(2)}</h2>'
                    content = content.replace(old_h1, new_h2, 1)
                    enhancements_made.append(f'Converted H1 #{i+1} to H2')
            
            # Enhance heading typography
            heading_enhancements = [
                (r'<h1([^>]*)>', r'<h1\1 className="text-4xl font-bold text-gray-900 mb-6">'),
                (r'<h2([^>]*)>', r'<h2\1 className="text-2xl font-semibold text-gray-800 mb-4">'),
                (r'<h3([^>]*)>', r'<h3\1 className="text-xl font-semibold text-gray-800 mb-3">')
            ]
            
            for pattern, replacement in heading_enhancements:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    enhancements_made.append('Enhanced heading typography')
            
            # Write changes if any enhancements were made
            if enhancements_made:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.enhancements_applied.append({
                    'file': file_path,
                    'backup': backup_path,
                    'enhancements': enhancements_made,
                    'type': 'heading_hierarchy',
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"✅ Enhanced heading hierarchy in {os.path.basename(file_path)}")
                for enhancement in enhancements_made:
                    print(f"   • {enhancement}")
            
            self.files_processed.append(file_path)
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    def enhance_content_flow(self, file_path):
        """Enhance content flow by breaking up walls of text"""
        try:
            # Create backup
            backup_path = self.create_backup(file_path)
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            enhancements_made = []
            
            # Find long paragraphs and add spacing
            paragraph_pattern = r'<p[^>]*>([^<]+)</p>'
            paragraphs = re.findall(paragraph_pattern, content)
            
            for paragraph in paragraphs:
                if len(paragraph.split()) > 50:  # Long paragraph
                    # Add spacing classes to paragraph
                    content = re.sub(
                        r'<p([^>]*)>([^<]+)</p>',
                        r'<p\1 className="mb-4 leading-relaxed">\2</p>',
                        content,
                        count=1
                    )
                    enhancements_made.append('Added spacing to long paragraph')
            
            # Add spacing between sections
            if '<div' in content and 'className=' in content:
                # Add margin classes to divs
                content = re.sub(
                    r'<div([^>]*className="[^"]*)"([^>]*)>',
                    r'<div\1 mb-6"\2>',
                    content
                )
                enhancements_made.append('Added section spacing')
            
            # Write changes if any enhancements were made
            if enhancements_made:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.enhancements_applied.append({
                    'file': file_path,
                    'backup': backup_path,
                    'enhancements': enhancements_made,
                    'type': 'content_flow',
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"✅ Enhanced content flow in {os.path.basename(file_path)}")
                for enhancement in enhancements_made:
                    print(f"   • {enhancement}")
            
            self.files_processed.append(file_path)
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    def enhance_css_system(self):
        """Enhance CSS system files with better typography"""
        css_files = [
            'responsive_typography_system.css',
            'mobile_spacing_system.css'
        ]
        
        for css_file in css_files:
            if os.path.exists(css_file):
                print(f"\n🔧 Enhancing {css_file}...")
                
                try:
                    # Create backup
                    backup_path = self.create_backup(css_file)
                    
                    # Read file content
                    with open(css_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    enhancements_made = []
                    
                    # Add enhanced line height utilities
                    if '--line-height-relaxed: 1.625' in content:
                        content = content.replace(
                            '--line-height-relaxed: 1.625',
                            '--line-height-relaxed: 1.7'
                        )
                        enhancements_made.append('Enhanced line-height-relaxed: 1.625 → 1.7')
                    
                    # Add mobile-specific typography enhancements
                    mobile_enhancements = """
/* Mobile Typography Enhancements */
@media (max-width: 768px) {
  .text-base {
    line-height: 1.7;
    letter-spacing: 0.01em;
  }
  
  .text-lg {
    line-height: 1.6;
    letter-spacing: 0.005em;
  }
  
  .text-xl {
    line-height: 1.5;
    letter-spacing: 0.002em;
  }
  
  /* Enhanced CTA typography */
  .btn, .button, .cta {
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: none;
  }
  
  /* Enhanced heading typography */
  h1, h2, h3 {
    letter-spacing: -0.01em;
    line-height: 1.2;
  }
}
"""
                    
                    if 'Mobile Typography Enhancements' not in content:
                        content += mobile_enhancements
                        enhancements_made.append('Added mobile typography enhancements')
                    
                    # Write changes if any enhancements were made
                    if enhancements_made:
                        with open(css_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        self.enhancements_applied.append({
                            'file': css_file,
                            'backup': backup_path,
                            'enhancements': enhancements_made,
                            'type': 'css_enhancement',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        print(f"✅ Enhanced {css_file}")
                        for enhancement in enhancements_made:
                            print(f"   • {enhancement}")
                    
                    self.files_processed.append(css_file)
                    
                except Exception as e:
                    print(f"❌ Error processing {css_file}: {e}")
    
    def process_react_components(self):
        """Process all React component files for Phase 2 enhancements"""
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
        files_with_enhancements = 0
        
        for directory in directories:
            if os.path.exists(directory):
                print(f"\n📁 Processing {directory} for Phase 2 enhancements...")
                
                # Find all TSX files in directory
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.tsx') or file.endswith('.ts'):
                            file_path = os.path.join(root, file)
                            total_files += 1
                            
                            # Check if file needs enhancements
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            enhancements_needed = []
                            
                            # Check for line height enhancements
                            if any(issue in content for issue in ['leading-tight', 'leading-snug', 'text-base']):
                                enhancements_needed.append('line_height')
                            
                            # Check for CTA enhancements
                            if any(cta in content for cta in ['btn', 'button', 'cta', '<a ']):
                                enhancements_needed.append('cta_typography')
                            
                            # Check for heading enhancements
                            if any(heading in content for heading in ['<h1', '<h2', '<h3']):
                                enhancements_needed.append('heading_hierarchy')
                            
                            # Check for content flow enhancements
                            if '<p>' in content and len(content) > 1000:
                                enhancements_needed.append('content_flow')
                            
                            # Apply enhancements
                            if enhancements_needed:
                                print(f"🔧 Enhancing {file}...")
                                
                                if 'line_height' in enhancements_needed:
                                    self.enhance_line_heights(file_path)
                                
                                if 'cta_typography' in enhancements_needed:
                                    self.enhance_cta_typography(file_path)
                                
                                if 'heading_hierarchy' in enhancements_needed:
                                    self.enhance_heading_hierarchy(file_path)
                                
                                if 'content_flow' in enhancements_needed:
                                    self.enhance_content_flow(file_path)
                                
                                files_with_enhancements += 1
        
        print(f"\n📊 Phase 2 Summary:")
        print(f"   • Total files processed: {total_files}")
        print(f"   • Files with enhancements: {files_with_enhancements}")
        print(f"   • Total enhancements applied: {len(self.enhancements_applied)}")
    
    def generate_report(self):
        """Generate a report of all Phase 2 enhancements applied"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 2 - Typography Enhancements',
            'summary': {
                'total_files_processed': len(self.files_processed),
                'total_enhancements_applied': len(self.enhancements_applied),
                'backup_directory': self.backup_dir
            },
            'enhancements': self.enhancements_applied
        }
        
        # Save report
        report_filename = f"phase2_enhancements_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Phase 2 report saved to: {report_filename}")
        print(f"📁 Backups saved to: {self.backup_dir}")
        
        return report

def main():
    """Main function to run Phase 2 typography enhancements"""
    print("🔧 Phase 2 Typography Enhancements")
    print("=" * 50)
    print("Implementing line heights, CTA typography, and heading hierarchy improvements")
    print("=" * 50)
    
    enhancer = Phase2TypographyEnhancer()
    
    # Enhance CSS system files
    enhancer.enhance_css_system()
    
    # Process React components
    enhancer.process_react_components()
    
    # Generate report
    report = enhancer.generate_report()
    
    print("\n" + "=" * 50)
    print("✅ PHASE 2 ENHANCEMENTS COMPLETE")
    print("=" * 50)
    
    print(f"📊 Summary:")
    print(f"   • Files processed: {report['summary']['total_files_processed']}")
    print(f"   • Enhancements applied: {report['summary']['total_enhancements_applied']}")
    print(f"   • Backup directory: {report['summary']['backup_directory']}")
    
    if report['enhancements']:
        print(f"\n🔧 Enhancements Applied:")
        for enhancement in report['enhancements']:
            print(f"   • {os.path.basename(enhancement['file'])}: {enhancement['type']}")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Test enhanced typography on mobile devices")
    print(f"   2. Verify improved readability and visual hierarchy")
    print(f"   3. Run accessibility tests")
    print(f"   4. Proceed to Phase 3 optimization if needed")

if __name__ == "__main__":
    main()
