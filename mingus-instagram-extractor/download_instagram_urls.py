#!/usr/bin/env python3
"""
Download Instagram content from the extracted URLs.
"""

import json
import sys
from pathlib import Path
from instagram_downloader import InstagramDownloader, ContentItem

def download_instagram_urls():
    """Download Instagram content from the extracted URLs."""
    
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
    
    print(f"✅ Found {len(urls)} Instagram URLs to download")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize downloader
    downloader = InstagramDownloader(output_dir=str(output_dir))
    
    # Convert URLs to ContentItem objects
    content_items = []
    for i, url in enumerate(urls, 1):
        print(f"📱 Preparing {i}/{len(urls)}: {url}")
        content_item = ContentItem(
            url=url,
            category="instagram",
            caption=f"Instagram Content {i}",
            original_note_id=f"note_{i}"
        )
        content_items.append(content_item)
    
    print(f"\n🚀 Starting download of {len(content_items)} items...")
    
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
    sys.exit(download_instagram_urls())
