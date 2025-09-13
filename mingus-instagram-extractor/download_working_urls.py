#!/usr/bin/env python3
"""
Download Instagram content from URLs that are actually accessible.
"""

import json
import subprocess
import sys
from pathlib import Path
from instagram_downloader import InstagramDownloader, ContentItem

def test_url_accessibility(url):
    """Test if a URL is accessible and downloadable."""
    try:
        # Quick test with yt-dlp to see if the URL is accessible
        cmd = [
            'yt-dlp',
            '--no-playlist',
            '--simulate',  # Don't actually download, just test
            '--quiet',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
        
    except Exception as e:
        print(f"   ❌ Error testing {url}: {e}")
        return False

def download_working_urls():
    """Download Instagram content from URLs that are accessible."""
    
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
    
    # Test each URL for accessibility
    print("\n🧪 Testing URL accessibility...")
    working_urls = []
    
    for i, url in enumerate(urls, 1):
        print(f"   Testing {i}/{len(urls)}: {url[:50]}...")
        if test_url_accessibility(url):
            working_urls.append(url)
            print(f"   ✅ Accessible")
        else:
            print(f"   ❌ Not accessible")
    
    print(f"\n📊 Results: {len(working_urls)}/{len(urls)} URLs are accessible")
    
    if not working_urls:
        print("❌ No accessible URLs found!")
        return 1
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Create instagram category directories
    (output_dir / "images" / "instagram").mkdir(parents=True, exist_ok=True)
    (output_dir / "videos" / "instagram").mkdir(parents=True, exist_ok=True)
    
    # Initialize downloader
    downloader = InstagramDownloader(output_dir=str(output_dir))
    
    # Convert working URLs to ContentItem objects
    content_items = []
    for i, url in enumerate(working_urls, 1):
        print(f"📱 Preparing {i}/{len(working_urls)}: {url}")
        content_item = ContentItem(
            url=url,
            category="instagram",
            caption=f"Instagram Content {i}",
            original_note_id=f"note_{i}"
        )
        content_items.append(content_item)
    
    print(f"\n🚀 Starting download of {len(content_items)} working URLs...")
    
    # Download content
    try:
        results = downloader.download_all_content(content_items)
        
        print(f"\n✅ Download completed!")
        print(f"   📁 Output directory: {output_dir.absolute()}")
        print(f"   📊 Results: {results}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(download_working_urls())
