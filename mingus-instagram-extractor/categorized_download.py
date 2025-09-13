#!/usr/bin/env python3
"""
Download Instagram content with keyword-based categorization.
"""

import json
import subprocess
import sys
from pathlib import Path
from enhanced_local_notes_processor import EnhancedLocalNotesProcessor

def download_categorized_content():
    """Download Instagram content with categorization."""
    
    print("🔍 Processing local notes with keyword categorization...")
    
    # Initialize enhanced processor
    processor = EnhancedLocalNotesProcessor()
    result = processor.process_all_local_notes()
    
    if not result['success']:
        print(f"❌ Processing failed: {result['error_message']}")
        return 1
    
    print(f"✅ Processed {result['total_notes']} notes")
    print(f"📊 Category breakdown: {result['category_breakdown']}")
    
    # Load the previously extracted Instagram URLs
    urls_file = Path("extracted_content/instagram_urls_20250912_211746.json")
    
    if not urls_file.exists():
        print("❌ Instagram URLs file not found!")
        return 1
    
    print("\n🔍 Loading Instagram URLs...")
    
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls_data = json.load(f)
    
    urls = urls_data.get('all_urls', [])
    if not urls:
        print("❌ No Instagram URLs found in file!")
        return 1
    
    print(f"✅ Found {len(urls)} Instagram URLs")
    
    # Create output directories for each category
    output_dir = Path("output")
    categories = ['faith', 'work_life', 'friendships', 'children', 'relationships', 'going_out', 'uncategorized']
    
    for category in categories:
        (output_dir / "videos" / category).mkdir(parents=True, exist_ok=True)
        (output_dir / "images" / category).mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    # Download each URL and categorize it
    successful_downloads = 0
    failed_downloads = 0
    categorized_downloads = {}
    
    for i, url in enumerate(urls, 1):
        print(f"\n📱 Downloading {i}/{len(urls)}: {url}")
        
        # Determine category based on URL content (simple heuristic)
        category = 'uncategorized'
        if any(keyword in url.lower() for keyword in ['faith', 'jesus', 'god', 'church', 'bible']):
            category = 'faith'
        elif any(keyword in url.lower() for keyword in ['work', 'business', 'career', 'job']):
            category = 'work_life'
        elif any(keyword in url.lower() for keyword in ['friend', 'social', 'party', 'hangout']):
            category = 'friendships'
        elif any(keyword in url.lower() for keyword in ['child', 'kid', 'baby', 'family']):
            category = 'children'
        elif any(keyword in url.lower() for keyword in ['love', 'relationship', 'couple', 'romance']):
            category = 'relationships'
        elif any(keyword in url.lower() for keyword in ['travel', 'trip', 'adventure', 'outdoor']):
            category = 'going_out'
        
        print(f"   🏷️  Categorized as: {category}")
        
        try:
            # Determine if it's likely a video (reel) or image (post)
            if '/reel/' in url:
                target_dir = output_dir / "videos" / category
            else:
                target_dir = output_dir / "images" / category
            
            # Download using yt-dlp
            cmd = [
                'yt-dlp',
                '--no-playlist',
                '--write-info-json',
                '--write-thumbnail',
                '--output', str(target_dir / '%(title)s.%(ext)s'),
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"   ✅ Success")
                successful_downloads += 1
                categorized_downloads[category] = categorized_downloads.get(category, 0) + 1
            else:
                print(f"   ❌ Failed: {result.stderr[:100]}...")
                failed_downloads += 1
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout")
            failed_downloads += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed_downloads += 1
    
    # Summary
    print(f"\n🎉 Download Summary:")
    print(f"   ✅ Successful: {successful_downloads}")
    print(f"   ❌ Failed: {failed_downloads}")
    print(f"   📁 Files saved to: {output_dir.absolute()}")
    
    print(f"\n🏷️  Categorized Downloads:")
    for category, count in categorized_downloads.items():
        print(f"   • {category}: {count} files")
    
    # Show what was downloaded by category
    print(f"\n📁 Downloaded files by category:")
    for category in categories:
        category_dir = output_dir / "videos" / category
        if category_dir.exists():
            files = list(category_dir.glob("*"))
            if files:
                print(f"\n   📂 {category}/videos/ ({len(files)} files):")
                for file_path in sorted(files):
                    if file_path.is_file() and not file_path.name.endswith('.json'):
                        size = file_path.stat().st_size
                        size_str = f"{size/1024/1024:.1f}MB" if size > 1024*1024 else f"{size/1024:.1f}KB"
                        print(f"      📄 {file_path.name} ({size_str})")
        
        category_dir = output_dir / "images" / category
        if category_dir.exists():
            files = list(category_dir.glob("*"))
            if files:
                print(f"\n   📂 {category}/images/ ({len(files)} files):")
                for file_path in sorted(files):
                    if file_path.is_file() and not file_path.name.endswith('.json'):
                        size = file_path.stat().st_size
                        size_str = f"{size/1024/1024:.1f}MB" if size > 1024*1024 else f"{size/1024:.1f}KB"
                        print(f"      📄 {file_path.name} ({size_str})")
    
    return 0 if successful_downloads > 0 else 1

if __name__ == "__main__":
    sys.exit(download_categorized_content())
