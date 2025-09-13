#!/usr/bin/env python3
"""
Test downloading a single Instagram URL.
"""

import sys
from pathlib import Path
from instagram_downloader import InstagramDownloader, ContentItem

def test_single_download():
    """Test downloading a single Instagram URL."""
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Create instagram category directories
    (output_dir / "images" / "instagram").mkdir(parents=True, exist_ok=True)
    (output_dir / "videos" / "instagram").mkdir(parents=True, exist_ok=True)
    
    # Initialize downloader
    downloader = InstagramDownloader(output_dir=str(output_dir))
    
    # Test with a single URL
    test_url = "https://www.instagram.com/p/DOJjLIxDRZr/"
    print(f"🧪 Testing download with: {test_url}")
    
    content_item = ContentItem(
        url=test_url,
        category="instagram",
        caption="Test Instagram Post",
        original_note_id="test_1"
    )
    
    try:
        print("🚀 Starting download...")
        result = downloader.download_content(content_item)
        
        print(f"✅ Download result: {result}")
        print(f"   Success: {result.success}")
        print(f"   File path: {result.file_path}")
        print(f"   Error: {result.error}")
        
        return 0 if result.success else 1
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_single_download())