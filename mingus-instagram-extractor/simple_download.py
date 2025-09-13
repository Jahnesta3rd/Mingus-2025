#!/usr/bin/env python3
"""
Simple script to download Instagram content directly using yt-dlp.
"""

import json
import subprocess
import sys
from pathlib import Path

def download_instagram_content():
    """Download Instagram content using yt-dlp directly."""
    
    # Path to the file with Instagram URLs
    urls_file = Path("extracted_content/instagram_urls_20250912_211746.json")
    
    if not urls_file.exists():
        print("❌ Instagram URLs file not found!")
        return 1
    
    print("🔍 Loading Instagram URLs...")
    
    # Load the URLs
    with open(urls_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    urls = data.get('all_urls', [])
    if not urls:
        print("❌ No Instagram URLs found in file!")
        return 1
    
    print(f"✅ Found {len(urls)} Instagram URLs")
    
    # Create output directories
    output_dir = Path("output")
    videos_dir = output_dir / "videos" / "instagram"
    images_dir = output_dir / "images" / "instagram"
    
    videos_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    # Download each URL
    successful_downloads = 0
    failed_downloads = 0
    
    for i, url in enumerate(urls, 1):
        print(f"\n📱 Downloading {i}/{len(urls)}: {url}")
        
        try:
            # Determine if it's likely a video (reel) or image (post)
            if '/reel/' in url:
                target_dir = videos_dir
            else:
                target_dir = images_dir
            
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
    
    # Show what was downloaded
    print(f"\n📁 Downloaded files:")
    for file_path in sorted(output_dir.rglob("*")):
        if file_path.is_file() and not file_path.name.endswith('.json'):
            size = file_path.stat().st_size
            size_str = f"{size/1024/1024:.1f}MB" if size > 1024*1024 else f"{size/1024:.1f}KB"
            print(f"   📄 {file_path.relative_to(output_dir)} ({size_str})")
    
    return 0 if successful_downloads > 0 else 1

if __name__ == "__main__":
    sys.exit(download_instagram_content())
